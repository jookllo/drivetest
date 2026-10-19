<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Validator;

class ListSignsRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        $subcategories = collect(config('signs.classes'))->flatMap(fn (array $class): array => array_keys($class['subcategories']))->all();

        return [
            'class' => ['sometimes', Rule::in(array_keys(config('signs.classes')))],
            'subcategory' => ['sometimes', Rule::in($subcategories)],
            'search' => ['sometimes', 'string', 'max:100'],
            'per_page' => ['sometimes', 'integer', 'min:1', 'max:100'],
            'page' => ['sometimes', 'integer', 'min:1'],
        ];
    }

    public function after(): array
    {
        return [function (Validator $validator): void {
            if ($validator->errors()->isNotEmpty()) {
                return;
            }
            if ($this->filled('class') && $this->filled('subcategory') && ! array_key_exists($this->input('subcategory'), config('signs.classes.'.$this->input('class').'.subcategories', []))) {
                $validator->errors()->add('subcategory', 'This subcategory does not belong to the selected class.');
            }
        }];
    }
}
