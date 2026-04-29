<?php

namespace App\Console\Commands;

use App\Models\Country;
use App\Repositories\NeighborhoodRepository;
use App\Repositories\ProvinceRepository;
use App\Repositories\StateRepository;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\TransferException;
use Illuminate\Console\Command;

class ScrapePttAddress2Command extends Command
{
    protected $signature = 'scrape:ptt-address2';

    protected $description = 'PTT posta kodu API verilerini state / province / neighborhood tablosuna yazar';

    private Client $client;

    private int $totalStates = 0;

    private int $totalProvinces = 0;

    private int $totalNeighborhoods = 0;

    public function __construct(
        private StateRepository $stateRepository,
        private ProvinceRepository $provinceRepository,
        private NeighborhoodRepository $neighborhoodRepository,
    ) {
        parent::__construct();

        $this->client = new Client([
            'base_uri' => 'https://www.ptt.gov.tr',
            'verify' => false,
            'timeout' => 60,
            'connect_timeout' => 15,
            'http_errors' => true,
            'headers' => [
                'Accept' => 'application/json',
                'Content-Type' => 'application/json',
                'Expect' => '',
                'Connection' => 'keep-alive',
                'User-Agent' => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ],
            'curl' => [
                CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
                CURLOPT_TCP_KEEPALIVE => 1,
            ],
        ]);
    }

    public function handle(): int
    {
        $this->output->title('PTT Adres Verisi (v2) Çekme İşlemi Başlatılıyor');

        try {
            $country = Country::firstOrCreate(['name' => 'Türkiye']);
            $iller = $this->fetchIller();

            $this->totalStates = count($iller);
            $stateProgress = $this->output->createProgressBar($this->totalStates);
            $stateProgress->start();

            foreach ($iller as $il) {
                $ilKodu = (string) $il['kod'];
                $ilAdi = $this->cleanText((string) $il['ad']);

                $state = $this->stateRepository->findOrCreateBySourceId(
                    $ilKodu,
                    [
                        'name' => $ilAdi,
                        'country_id' => $country->id,
                    ]
                );

                $ilceler = $this->fetchIlceler($ilKodu);

                foreach ($ilceler as $ilce) {
                    $ilceKodu = (string) $ilce['kod'];
                    $ilceAdi = $this->cleanText((string) $ilce['ad']);
                    $provinceSourceId = $ilKodu.'_'.$ilceKodu;

                    $province = $this->provinceRepository->findOrCreateBySourceId(
                        $provinceSourceId,
                        [
                            'name' => $ilceAdi,
                            'country_id' => $country->id,
                            'state_id' => $state->id,
                        ]
                    );

                    $this->totalProvinces++;

                    $postaKodlari = $this->fetchPostaKodlari($ilKodu, $ilceKodu);

                    /** @var array<string, bool> $seenNeighborhoods */
                    $seenNeighborhoods = [];

                    foreach ($postaKodlari as $row) {
                        $mahalleAdi = $this->cleanText((string) ($row['mahalleAdi'] ?? ''));

                        if ($mahalleAdi === '') {
                            continue;
                        }

                        $postaKodu = trim((string) ($row['posta_Kodu'] ?? $row['posta_kodu'] ?? ''));
                        $uniqueKey = mb_strtoupper($mahalleAdi, 'UTF-8').'|'.$postaKodu;

                        if (isset($seenNeighborhoods[$uniqueKey])) {
                            continue;
                        }

                        $seenNeighborhoods[$uniqueKey] = true;

                        $neighborhoodSourceId = $provinceSourceId.'_'.md5($uniqueKey);

                        $this->neighborhoodRepository->findOrCreateBySourceId(
                            $neighborhoodSourceId,
                            [
                                'name' => $mahalleAdi,
                                'country_id' => $country->id,
                                'state_id' => $state->id,
                                'province_id' => $province->id,
                                'posta_kodu' => $postaKodu !== '' ? $postaKodu : null,
                            ]
                        );

                        $this->totalNeighborhoods++;
                    }
                }

                $stateProgress->advance();
                usleep(120000);
            }

            $stateProgress->finish();

            $this->newLine(2);
            $this->info(sprintf(
                'Tamamlandı: %d il, %d ilçe, %d mahalle işlendi.',
                $this->totalStates,
                $this->totalProvinces,
                $this->totalNeighborhoods
            ));

            return self::SUCCESS;
        } catch (\Throwable $throwable) {
            $this->newLine();
            $this->error('Hata: '.$throwable->getMessage());

            return self::FAILURE;
        }
    }

    private function fetchIller(): array
    {
        $data = $this->callApi('iller');

        return array_values(array_filter($data, static fn (array $il): bool => (int) ($il['kod'] ?? 0) > 0));
    }

    private function fetchIlceler(string $ilKodu): array
    {
        $data = $this->callApi('ilceler', ['il_kodu' => $ilKodu]);

        return array_values(array_filter($data, static fn (array $ilce): bool => (int) ($ilce['kod'] ?? 0) > 0));
    }

    private function fetchPostaKodlari(string $ilKodu, string $ilceKodu): array
    {
        $data = $this->callApi('postakodu', [
            'il_kodu' => $ilKodu,
            'ilce_kodu' => $ilceKodu,
        ]);

        return array_values(array_filter($data, static fn (array $row): bool => isset($row['mahalleAdi'])));
    }

    /**
     * PTT sitesindeki çerez banner’ı (“Anladım”) yalnızca tarayıcıda çalışır; bu komut doğrudan
     * /api/posta-kodu çağırır, cookie gerektirmez. cURL 56 / SSL unexpected EOF gibi kopmalar için
     * HTTP/1.1 + yeniden deneme kullanılır.
     */
    private function callApi(string $action, array $params = []): array
    {
        $maxAttempts = 6;
        $lastException = null;

        for ($attempt = 1; $attempt <= $maxAttempts; $attempt++) {
            try {
                $response = $this->client->post('/api/posta-kodu', [
                    'json' => ['action' => $action, ...$params],
                ]);

                $payload = json_decode((string) $response->getBody(), true);

                if (! is_array($payload)) {
                    throw new \RuntimeException("Beklenmeyen API cevabı: {$action}");
                }

                if (array_key_exists('error', $payload)) {
                    $message = (string) $payload['error'];
                    throw new \RuntimeException("PTT API hatası ({$action}): {$message}");
                }

                return $payload;
            } catch (TransferException $exception) {
                $lastException = $exception;

                if ($attempt >= $maxAttempts) {
                    break;
                }

                $delayMs = min(30_000, (int) (500 * (2 ** ($attempt - 1))) + random_int(0, 500));
                if ($this->output->isVerbose()) {
                    $this->warn(sprintf(
                        'PTT API bağlantı hatası (%s), %d ms sonra tekrar deneniyor (%d/%d): %s',
                        $action,
                        $delayMs,
                        $attempt,
                        $maxAttempts,
                        $exception->getMessage()
                    ));
                }
                usleep($delayMs * 1000);
            }
        }

        throw $lastException ?? new \RuntimeException("PTT API çağrısı başarısız: {$action}");
    }

    private function cleanText(string $text): string
    {
        $text = html_entity_decode($text, ENT_QUOTES | ENT_HTML5, 'UTF-8');
        $text = trim(preg_replace('/\s+/', ' ', $text) ?? '');

        return $this->capitalizeFirstLetter($text);
    }

    private function capitalizeFirstLetter(string $string): string
    {
        $turkishLowercase = [
            'İ' => 'i',
            'I' => 'ı',
            'Ğ' => 'ğ',
            'Ş' => 'ş',
            'Ç' => 'ç',
            'Ö' => 'ö',
            'Ü' => 'ü',
        ];

        $words = preg_split('/\s+/', trim($string)) ?: [];
        $capitalizedWords = [];

        foreach ($words as $word) {
            if ($word === '') {
                continue;
            }

            $firstChar = mb_substr($word, 0, 1, 'UTF-8');
            $rest = mb_substr($word, 1, null, 'UTF-8');
            $restLowercased = '';

            for ($index = 0; $index < mb_strlen($rest, 'UTF-8'); $index++) {
                $char = mb_substr($rest, $index, 1, 'UTF-8');
                $restLowercased .= $turkishLowercase[$char] ?? mb_strtolower($char, 'UTF-8');
            }

            $capitalizedWords[] = $firstChar.$restLowercased;
        }

        return implode(' ', $capitalizedWords);
    }
}
