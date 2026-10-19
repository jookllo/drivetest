<?php

namespace App\Console\Commands;

use App\Models\QuizAttempt;
use App\Services\QuizEngine;
use Illuminate\Console\Command;

class ExpireQuizAttempts extends Command
{
    protected $signature = 'quiz:expire';

    protected $description = 'Finalise expired guest attempts using their last accepted answers';

    public function handle(QuizEngine $engine): int
    {
        $count = 0;
        QuizAttempt::where('status', 'active')->where('expires_at', '<=', now())->chunkById(100, function ($attempts) use ($engine, &$count): void {
            foreach ($attempts as $attempt) {
                $engine->access($attempt->id, $attempt->owner_hash);
                $count++;
            }
        });
        $this->info($count.' expired attempt(s) processed.');

        return self::SUCCESS;
    }
}
