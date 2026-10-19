<?php

namespace Tests\Feature;

use Tests\TestCase;

class QuizPageTest extends TestCase
{
    public function test_the_quiz_page_is_served_with_its_assets(): void
    {
        $response = $this->get('/quiz');

        $response->assertOk();
        $response->assertSee('id="quiz-app"', false);
        $response->assertSee('assets/quiz/quiz.css', false);
        $response->assertSee('vendor/vue.global.prod.js', false);
        $response->assertSee('assets/quiz/app.js', false);
    }

    public function test_the_quiz_page_answers_at_the_site_root(): void
    {
        $this->get('/')->assertOk();
    }

    public function test_local_demo_embeds_four_questions_without_a_database(): void
    {
        $this->app->instance('env', 'local');
        $this->get('/quiz?demo=1')->assertOk()
            ->assertSee('id="quiz-demo-data"', false)
            ->assertSee('data-demo-available="true"', false);

        $questions = json_decode(file_get_contents(resource_path('quiz-demo.json')), true, 512, JSON_THROW_ON_ERROR);
        $this->assertCount(4, $questions);
        foreach ($questions as $question) {
            $this->assertNotEmpty($question['correctIds']);
            $this->assertEmpty(array_diff($question['correctIds'], array_column($question['options'], 'id')));
        }
    }

    public function test_demo_data_is_not_exposed_in_production(): void
    {
        $this->app->instance('env', 'production');
        $this->get('https://localhost/quiz?demo=1')->assertOk()
            ->assertDontSee('id="quiz-demo-data"', false)
            ->assertSee('data-demo-available="false"', false);
    }

    public function test_non_loopback_local_requests_do_not_receive_demo_data(): void
    {
        $this->app->instance('env', 'local');
        $this->withServerVariables(['REMOTE_ADDR' => '192.0.2.10'])
            ->get('/quiz?demo=1')->assertOk()
            ->assertDontSee('id="quiz-demo-data"', false);
    }
}
