<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class SignSeeder extends Seeder
{
    public function run(): void
    {
        $this->command?->warn('No signs seeded: export the latest edited catalog before importing.');
    }
}
