<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Validation\ValidationException;

class AdminAuthController extends Controller
{
    public function session(Request $request): JsonResponse
    {
        return response()->json(['authenticated' => (bool) $request->user()?->is_admin, 'csrf_token' => csrf_token()]);
    }

    public function login(Request $request): JsonResponse
    {
        $data = $request->validate(['email' => 'required|email|max:255', 'password' => 'required|string|max:255']);
        if (! Auth::attempt($data + ['is_admin' => true])) {
            throw ValidationException::withMessages(['email' => 'The login details are not valid.']);
        }
        $request->session()->regenerate();

        return response()->json(['authenticated' => true, 'csrf_token' => csrf_token()]);
    }

    public function logout(Request $request): JsonResponse
    {
        Auth::logout();
        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return response()->json(['authenticated' => false, 'csrf_token' => csrf_token()]);
    }
}
