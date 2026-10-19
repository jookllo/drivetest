<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class SignResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        $class = $this->class_code ? config('signs.classes.'.$this->class_code) : null;

        return [
            'id' => $this->id,
            'name' => $this->name,
            'class' => $class ? ['code' => $this->class_code, 'name' => $class['name']] : null,
            'subcategory' => $this->subcategory_id ? [
                'id' => $this->subcategory_id,
                'name' => $class['subcategories'][$this->subcategory_id] ?? $this->subcategory_id,
            ] : null,
            'meaning' => $this->meaning,
            'image_url' => $this->image_path ? route($request->routeIs('api.preview.*') ? 'api.preview.signs.image' : 'api.signs.image', ['id' => $this->id]) : null,
            'status' => $this->status,
            'review_notes' => $this->when($request->routeIs('api.preview.*'), $this->review_notes),
        ];
    }
}
