<?php

namespace App\Console\Commands;

use App\Services\SignCatalogImport;
use Illuminate\Console\Command;

class ImportSigns extends Command
{
    protected $signature = 'signs:import {file : Absolute path to exported JSON} {--dry-run : Validate and summarize without writing}';

    protected $description = 'Import edited names and known vector artwork as review drafts';

    public function handle(SignCatalogImport $importer): int
    {
        $file = $this->argument('file');
        if (! is_file($file) || ! is_readable($file)) {
            $this->error('Export file not found or unreadable.');

            return self::FAILURE;
        }
        try {
            $rows = $importer->prepare($file);
        } catch (\JsonException|\InvalidArgumentException $error) {
            $this->error($error->getMessage());

            return self::FAILURE;
        }
        $this->table(['Class', 'Count'], collect($rows)->countBy(fn (array $row): string => $row['class_code'] ?? 'Unassigned')->map(fn (int $count, string $code): array => [$code, $count])->values()->all());
        $review = collect($rows)->filter(fn (array $row): bool => $row['class_code'] === null || ($row['class_code'] !== 'B' && $row['subcategory_id'] === null))->count();
        $this->info(count($rows).' names validated; '.$review.' classifications need review.');
        if (! $this->option('dry-run')) {
            $importer->import($rows);
            $this->info('Imported as drafts. Existing IDs updated; absent records were not deleted.');
        }

        return self::SUCCESS;
    }
}
