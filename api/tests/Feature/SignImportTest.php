<?php

namespace Tests\Feature;

use App\Services\SignCatalogImport;
use Tests\TestCase;

class SignImportTest extends TestCase
{
    public function test_export_preserves_all_names_and_maps_classes_conservatively(): void
    {
        $service = new SignCatalogImport;
        $source = json_decode(file_get_contents(base_path('../sign-labels.json')), true);
        $rows = $service->prepare(base_path('../sign-labels.json'));
        $this->assertCount(count($source), $rows);
        $this->assertSame(array_column($source, 'label'), array_column($rows, 'name'));
        $this->assertSame(['A', 'priority'], $service->classify('R01'));
        $this->assertSame(['A', 'compulsory'], $service->classify('M01'));
        $this->assertSame(['C', 'facility'], $service->classify('I04'));
        $this->assertSame(['B', null], $service->classify('W28A'));
        $this->assertSame(['A', null], $service->classify('M10'));
        $this->assertSame([null, null], $service->classify('W35A'));
    }

    public function test_duplicate_export_ids_are_rejected(): void
    {
        $row = json_decode(file_get_contents(base_path('../sign-labels.json')), true)[0];
        $file = tempnam(sys_get_temp_dir(), 'sign-import-');
        try {
            file_put_contents($file, json_encode([$row, $row]));
            $this->expectException(\InvalidArgumentException::class);
            (new SignCatalogImport)->prepare($file);
        } finally {
            unlink($file);
        }
    }

    public function test_preview_is_not_accessible_outside_local_environment(): void
    {
        $this->getJson('/api/v1/preview/signs')->assertNotFound();
        $this->getJson('/api/v1/preview/signs/r01-stop/image')->assertNotFound();
    }
}
