<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Validator;

class StartQuizRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'mode' => ['required', Rule::in(['practice', 'challenge'])],
            'topic' => ['required', Rule::in(array_merge(['mixed'], array_keys(config('quiz.topics'))))],
            'length' => ['required', 'integer', Rule::in(config('quiz.lengths'))],
            'class' => ['nullable', Rule::in(['A', 'B', 'C'])],
            'subcategory' => ['nullable', 'string', 'max:40'],
        ];
    }

    public function after(): array
    {
        return [function (Validator $validator): void {
            if ($this->input('mode') === 'challenge' && (int) $this->input('length') !== 10) {
                $validator->errors()->add('length', 'Timed challenges contain 10 questions.');
            }
            if ($this->filled('class') && $this->input('topic') === 'classes') {
                $validator->errors()->add('topic', 'Choose all classes for a class-identification quiz.');
            }
            if ($this->filled('subcategory') && ! array_key_exists($this->input('subcategory'), config('signs.classes.'.$this->input('class').'.subcategories', []))) {
                $validator->errors()->add('subcategory', 'Choose a subcategory belonging to the selected class.');
            }
        }];
    }
}
