<?php

namespace Database\Seeders;

use App\Models\Question;
use App\Models\User;
use Illuminate\Database\Seeder;

class QuizBrowserSeeder extends Seeder
{
    public function run(): void
    {
        if (config('database.connections.mysql.database') !== 'drivetest_test') {
            throw new \RuntimeException('Browser fixtures require drivetest_test.');
        }
        User::firstOrCreate(['email' => 'editor@example.test'], ['name' => 'Test editor', 'password' => 'local-browser-test-only']);
        User::where('email', 'editor@example.test')->update(['is_admin' => true]);
        foreach (['names', 'classes', 'subcategories', 'general'] as $topic) {
            for ($i = 1; $i <= 20; $i++) {
                Question::firstOrCreate(['prompt' => "Browser fixture {$topic} {$i}: choose A"], ['topic' => $topic, 'type' => 'single', 'options' => [['id' => 'a', 'label' => 'A'], ['id' => 'b', 'label' => 'B']], 'correct_ids' => ['a'], 'explanation' => 'A is the expected answer for this isolated browser fixture.', 'status' => 'published', 'reviewed_at' => now(), 'shuffle_options' => true, 'group_order' => 0, 'class_code' => $topic === 'subcategories' ? 'A' : null, 'subcategory_id' => $topic === 'subcategories' ? 'priority' : null]);
            }
        }
    }
}
