<?php

namespace Tests\Feature;

use App\Http\Resources\SignResource;
use App\Models\Sign;
use Illuminate\Http\Request;
use Tests\TestCase;

class SignApiTest extends TestCase
{
    public function test_classes_expose_the_confirmed_taxonomy(): void
    {
        $this->getJson('/api/v1/classes')->assertOk()
            ->assertJsonPath('data.0.code', 'A')
            ->assertJsonPath('data.0.subcategories.0.id', 'priority')
            ->assertJsonPath('data.1.code', 'B')
            ->assertJsonPath('data.1.subcategories', [])
            ->assertJsonPath('data.2.code', 'C')
            ->assertJsonPath('data.2.subcategories.2.id', 'facility');
    }

    public function test_invalid_filters_are_rejected_before_database_access(): void
    {
        $this->getJson('/api/v1/signs?class=B&subcategory=priority')->assertUnprocessable()->assertJsonValidationErrors('subcategory');
        $this->getJson('/api/v1/signs?per_page=101')->assertUnprocessable()->assertJsonValidationErrors('per_page');
        $this->getJson('/api/v1/signs?class=D')->assertUnprocessable()->assertJsonValidationErrors('class');
    }

    public function test_resource_preserves_edited_names_without_exposing_editor_notes(): void
    {
        $sign = Sign::factory()->make(['name' => 'My edited sign ahead', 'review_notes' => 'Private notes']);
        $data = (new SignResource($sign))->resolve(Request::create('/api/v1/signs/example'));
        $this->assertSame('My edited sign ahead', $data['name']);
        $this->assertSame('B', $data['class']['code']);
        $this->assertNull($data['subcategory']);
        $this->assertArrayNotHasKey('review_notes', $data);
        $this->assertArrayNotHasKey('quiz_answer', $data);
    }
}
