<?php

namespace App\Services;

use App\Models\Sign;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Storage;
use InvalidArgumentException;

class SignCatalogImport
{
    public function prepare(string $file): array
    {
        $rows = json_decode(file_get_contents($file), true, 512, JSON_THROW_ON_ERROR);
        if (! is_array($rows) || ! array_is_list($rows) || count($rows) === 0) {
            throw new InvalidArgumentException('Expected a non-empty JSON array.');
        }
        $manifest = collect(json_decode(file_get_contents(base_path('../signs/manifest.json')), true, 512, JSON_THROW_ON_ERROR))->keyBy('id');
        $seen = [];
        $prepared = [];
        foreach ($rows as $row) {
            $id = $row['id'] ?? null;
            $name = $row['label'] ?? $row['name'] ?? null;
            if (! is_string($id) || ! $manifest->has($id) || isset($seen[$id]) || ! is_string($name) || trim($name) === '' || mb_strlen($name) > 255) {
                throw new InvalidArgumentException('Unknown/duplicate ID or invalid sign name. No rows imported.');
            }
            $seen[$id] = true;
            $original = $manifest[$id];
            $source = realpath(base_path('../signs/'.$original['svg']));
            if (! $source || ! is_file($source)) {
                throw new InvalidArgumentException('Missing source artwork for '.$id);
            }
            if (isset($row['svg']) && $row['svg'] !== $original['svg']) {
                throw new InvalidArgumentException('Changed artwork requires separate review: '.$id);
            }
            if (isset($row['svg_path']) && $row['svg_path'] !== 'signs/'.$original['svg']) {
                throw new InvalidArgumentException('Changed artwork requires separate review: '.$id);
            }
            [$class, $subcategory] = $this->classify($original['code']);
            $notes = $row['notes'] ?? $original['notes'];
            if (! is_string($notes)) {
                throw new InvalidArgumentException('Review notes must be text.');
            }
            $notes .= '\nImported from edited catalog; artwork and meanings remain unverified.';
            if ($class === null || ($class !== 'B' && $subcategory === null)) {
                $notes .= '\nClassification requires review; no subcategory guessed.';
            }
            $prepared[] = [
                'id' => $id, 'name' => $name, 'class_code' => $class,
                'subcategory_id' => $subcategory, 'status' => 'draft',
                'image_path' => 'signs/'.$id.'.svg', 'review_notes' => $notes,
                'source_file' => $source,
            ];
        }

        return $prepared;
    }

    public function classify(string $code): array
    {
        if (preg_match('/^W(0[1-9]|[12][0-9]|3[0-4]|13A|13B|28A|28B)$/', $code)) {
            return ['B', null];
        }
        if (in_array($code, ['R01', 'R02'], true)) {
            return ['A', 'priority'];
        }
        if (preg_match('/^M/', $code) || $code === 'EX01') {
            return ['A', $code === 'M10' ? null : 'compulsory'];
        }
        if (preg_match('/^P/', $code)) {
            return ['A', in_array($code, ['P26', 'P27', 'P28', 'P29'], true) ? null : 'prohibitory'];
        }
        if (preg_match('/^I/', $code)) {
            $facilities = ['I01', 'I02', 'I04', 'I08', 'I13', 'I14', 'I16', 'I17', 'I18', 'I19', 'I20', 'I21', 'I22', 'I23', 'I24', 'I25', 'I26', 'I27', 'I28'];

            return ['C', in_array($code, $facilities, true) ? 'facility' : null];
        }
        if (preg_match('/^D/', $code) || in_array($code, ['S01', 'S02', 'S03'], true)) {
            if (in_array($code, ['D01', 'D02', 'D03', 'D04', 'D05', 'D06', 'D07', 'D08', 'D13'], true)) {
                return ['C', 'advance-directional'];
            }

            return ['C', in_array($code, ['D14', 'D17'], true) ? 'route-confirmatory' : null];
        }

        return [null, null];
    }

    public function import(array $rows): void
    {
        DB::transaction(function () use ($rows): void {
            foreach ($rows as $row) {
                $source = $row['source_file'];
                unset($row['source_file']);
                if (! Storage::disk('local')->put($row['image_path'], file_get_contents($source))) {
                    throw new \RuntimeException('Could not store artwork.');
                }
                Sign::updateOrCreate(['id' => $row['id']], $row);
            }
        });
    }
}
