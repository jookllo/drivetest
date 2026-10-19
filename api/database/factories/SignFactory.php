<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

class SignFactory extends Factory
{
    public function definition(): array
    {
        return [
            'id' => fake()->unique()->slug(),
            'name' => 'Bend left ahead',
            'class_code' => 'B',
            'subcategory_id' => null,
            'meaning' => 'Example draft sign.',
            'status' => 'draft',
        ];
    }
}
