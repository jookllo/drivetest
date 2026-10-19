<?php

namespace App\Http\Resources;

use App\Services\QuizEngine;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class QuizAttemptResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return app(QuizEngine::class)->present($this->resource);
    }
}
