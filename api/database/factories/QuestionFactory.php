<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

class QuestionFactory extends Factory
{
    public function definition(): array
    {
        return ['prompt' => fake()->sentence().'?', 'topic' => 'general', 'type' => 'single',
            'options' => [['id' => 'a', 'label' => 'First'], ['id' => 'b', 'label' => 'Second']],
            'correct_ids' => ['a'], 'explanation' => 'Reviewed explanation.', 'status' => 'draft', 'group_order' => 0, 'shuffle_options' => true, 'version' => 1];
    }

    public function published(): static
    {
        return $this->state(fn () => ['status' => 'published', 'reviewed_at' => now()]);
    }
}
