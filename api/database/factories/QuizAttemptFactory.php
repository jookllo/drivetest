<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Str;

class QuizAttemptFactory extends Factory
{
    public function definition(): array
    {
        return ['owner_hash' => hash('sha256', 'guest'), 'public_id' => (string) Str::uuid(), 'mode' => 'practice', 'topic' => 'general', 'filters' => [], 'items' => [], 'answers' => [], 'total' => 0, 'started_at' => now(), 'expires_at' => now()->addDay()];
    }
}
