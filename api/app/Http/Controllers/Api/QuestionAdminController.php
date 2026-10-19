<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\SaveQuestionRequest;
use App\Models\Question;
use App\Models\Sign;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Storage;
use Illuminate\Validation\Rule;
use Illuminate\Validation\ValidationException;
use Symfony\Component\HttpFoundation\BinaryFileResponse;

class QuestionAdminController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $data = $request->validate(['search' => 'nullable|string|max:100', 'page' => 'nullable|integer|min:1']);
        $query = Question::query()->latest();
        if (! empty($data['search'])) {
            $query->where('prompt', 'like', '%'.$data['search'].'%');
        }

        return response()->json($query->paginate(30));
    }

    public function save(SaveQuestionRequest $request, ?string $id = null): JsonResponse
    {
        $question = DB::transaction(function () use ($request, $id): Question {
            $question = $id ? Question::whereKey($id)->lockForUpdate()->firstOrFail() : new Question;
            if ($id && (int) $request->input('version') !== $question->version) {
                abort(409, 'This question changed. Reload it before saving.');
            }
            $data = $request->safe()->except(['reviewed', 'version']);
            $data['reviewed_at'] = $request->boolean('reviewed') ? now() : null;
            $data['version'] = $id ? $question->version + 1 : 1;
            $question->fill($data)->save();

            return $question;
        });

        return response()->json(['data' => $question], $id ? 200 : 201);
    }

    public function signs(): JsonResponse
    {
        return response()->json(['data' => Sign::orderBy('id')->get(), 'classes' => config('signs.classes')]);
    }

    public function sign(Request $request, string $id): JsonResponse
    {
        $data = $request->validate([
            'name' => 'required|string|max:255', 'meaning' => 'nullable|string|max:4000',
            'class_code' => ['nullable', Rule::in(['A', 'B', 'C'])], 'subcategory_id' => 'nullable|string|max:40',
            'status' => ['required', Rule::in(['draft', 'published'])], 'review_notes' => 'nullable|string|max:10000',
            'reviewed' => 'required|boolean', 'updated_at' => 'required|string',
        ]);
        if (! empty($data['subcategory_id']) && ! array_key_exists($data['subcategory_id'], config('signs.classes.'.($data['class_code'] ?? '').'.subcategories', []))) {
            throw ValidationException::withMessages(['subcategory_id' => 'Choose a subcategory in the selected class.']);
        }
        $sign = DB::transaction(function () use ($data, $id): Sign {
            $sign = Sign::whereKey($id)->lockForUpdate()->firstOrFail();
            if ($sign->updated_at->toJSON() !== $data['updated_at']) {
                abort(409, 'This sign changed. Reload before saving.');
            }
            if ($data['status'] === 'published' && (! $data['reviewed'] || empty($data['class_code']) || ! $sign->image_path || (in_array($data['class_code'], ['A', 'C']) && empty($data['subcategory_id'])))) {
                throw ValidationException::withMessages(['status' => 'Review artwork and classification, including the subcategory where applicable, before publishing.']);
            }
            unset($data['reviewed'],$data['updated_at']);
            $sign->fill($data);
            if ($sign->isDirty(['name', 'meaning', 'class_code', 'subcategory_id', 'status'])) {
                Question::where('sign_id', $id)->update(['status' => 'draft', 'reviewed_at' => null]);
            }
            $sign->save();

            return $sign;
        });

        return response()->json(['data' => $sign]);
    }

    public function image(string $id): BinaryFileResponse
    {
        $sign = Sign::findOrFail($id);
        abort_unless($sign->image_path && Storage::disk('local')->exists($sign->image_path), 404);

        return response()->file(Storage::disk('local')->path($sign->image_path), ['Content-Type' => 'image/svg+xml', 'Content-Security-Policy' => "default-src 'none'; style-src 'unsafe-inline'; sandbox", 'X-Content-Type-Options' => 'nosniff', 'Cache-Control' => 'private, no-store']);
    }
}
