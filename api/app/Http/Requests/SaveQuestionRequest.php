<?php

namespace App\Http\Requests;

use App\Models\Sign;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Validator;

class SaveQuestionRequest extends FormRequest
{
    public function authorize(): bool
    {
        return (bool) $this->user()?->is_admin;
    }

    public function rules(): array
    {
        return [
            'prompt' => ['required', 'string', 'max:2000'], 'topic' => ['required', Rule::in(array_keys(config('quiz.topics')))],
            'type' => ['required', Rule::in(['single', 'multi'])],
            'options' => ['required', 'array', 'min:2', 'max:6'], 'options.*' => ['required', 'array:id,label'],
            'options.*.id' => ['required', 'string', 'regex:/^[a-zA-Z0-9_-]+$/', 'max:40', 'distinct'],
            'options.*.label' => ['required', 'string', 'max:500', 'distinct'],
            'correct_ids' => ['required', 'array', 'min:1', 'max:6'], 'correct_ids.*' => ['required', 'string', 'distinct'],
            'explanation' => ['required', 'string', 'max:4000'], 'sign_id' => ['nullable', 'string', Rule::exists('signs', 'id')],
            'class_code' => ['nullable', Rule::in(['A', 'B', 'C'])], 'subcategory_id' => ['nullable', 'string', 'max:40'],
            'group_key' => ['nullable', 'string', 'max:80', 'regex:/^[a-zA-Z0-9_-]+$/'], 'group_order' => ['required', 'integer', 'min:0', 'max:100'],
            'shuffle_options' => ['required', 'boolean'], 'status' => ['required', Rule::in(['draft', 'published'])],
            'reviewed' => ['required', 'boolean'], 'source_notes' => ['nullable', 'string', 'max:10000'],
            'version' => ['sometimes', 'integer', 'min:1'],
        ];
    }

    public function after(): array
    {
        return [function (Validator $validator): void {
            if ($validator->errors()->isNotEmpty()) {
                return;
            }
            $correct = $this->input('correct_ids');
            if (array_diff($correct, array_column($this->input('options'), 'id')) || ($this->input('type') === 'single' && count($correct) !== 1)) {
                $validator->errors()->add('correct_ids', 'Select valid correct options (exactly one for single-answer questions).');
            }
            $sign = $this->filled('sign_id') ? Sign::find($this->input('sign_id')) : null;
            if ($sign && ($sign->class_code !== $this->input('class_code') || $sign->subcategory_id !== $this->input('subcategory_id'))) {
                $validator->errors()->add('sign_id', 'Question classification must match the linked sign.');
            }
            if ($this->filled('subcategory_id') && ! array_key_exists($this->input('subcategory_id'), config('signs.classes.'.$this->input('class_code').'.subcategories', []))) {
                $validator->errors()->add('subcategory_id', 'Subcategory must belong to the class.');
            }
            if ($this->input('topic') === 'subcategories' && ! $this->filled('subcategory_id')) {
                $validator->errors()->add('subcategory_id', 'A subcategory question requires an applicable subcategory.');
            }
            if ($this->input('status') === 'published' && (! $this->boolean('reviewed') || ($sign && ($sign->status !== 'published' || ! $sign->image_path)))) {
                $validator->errors()->add('status', 'Confirm content review and publish the linked sign with artwork before publishing this question.');
            }
        }];
    }
}
