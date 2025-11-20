<?php
declare(strict_types=1);

class HomeController {
    public function handle(): array {
        return [
            'welcomeMessage' => 'Welcome to AdSphere!',
            'featuredProducts' => ['R290 Heat Pump', 'R410a Pool Heater']
        ];
    }
}
