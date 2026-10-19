<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\ListSignsRequest;
use App\Http\Resources\SignResource;
use App\Models\Sign;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Support\Facades\Storage;
use Symfony\Component\HttpFoundation\BinaryFileResponse;

class SignController extends Controller
{
    public function classes(): JsonResponse
    {
        $classes = collect(config('signs.classes'))->map(function (array $class, string $code): array {
            return [
                'code' => $code,
                'name' => $class['name'],
                'subcategories' => collect($class['subcategories'])->map(fn (string $name, string $id): array => compact('id', 'name'))->values(),
            ];
        })->values();

        return response()->json(['data' => $classes]);
    }

    public function index(ListSignsRequest $request): AnonymousResourceCollection
    {
        $filters = $request->validated();
        $query = Sign::query();
        if (! $request->routeIs('api.preview.*')) {
            $query->where('status', 'published');
        }
        foreach (['class' => 'class_code', 'subcategory' => 'subcategory_id'] as $filter => $column) {
            if (isset($filters[$filter])) {
                $query->where($column, $filters[$filter]);
            }
        }
        if (isset($filters['search'])) {
            $query->where('name', 'like', '%'.$filters['search'].'%');
        }

        return SignResource::collection($query->orderBy('id')->paginate($filters['per_page'] ?? 20)->withQueryString());
    }

    public function show(Request $request, string $id): SignResource
    {
        return new SignResource(Sign::query()->when(! $request->routeIs('api.preview.*'), fn ($query) => $query->where('status', 'published'))->findOrFail($id));
    }

    public function image(Request $request, string $id): BinaryFileResponse
    {
        $sign = Sign::query()->when(! $request->routeIs('api.preview.*'), fn ($query) => $query->where('status', 'published'))->findOrFail($id);
        abort_unless($sign->image_path && Storage::disk('local')->exists($sign->image_path), 404);

        return response()->file(Storage::disk('local')->path($sign->image_path), [
            'Content-Type' => 'image/svg+xml',
            'Content-Security-Policy' => "default-src 'none'; style-src 'unsafe-inline'; sandbox",
            'X-Content-Type-Options' => 'nosniff',
            'Cache-Control' => 'private, no-store',
        ]);
    }
}
