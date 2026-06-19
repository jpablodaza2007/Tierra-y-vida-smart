import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { importProvidersFrom } from '@angular/core';
import {
  GoogleLoginProvider,
  GoogleSigninButtonModule,
  SOCIAL_AUTH_CONFIG,
  SocialAuthServiceConfig
} from '@abacritt/angularx-social-login';

import { AppComponent } from './app/app';
import { routes } from './app/app.routes';
import { authInterceptor } from './app/services/auth.interceptor';

const GOOGLE_CLIENT_ID =
  '310711929084-e96ibrd6ns8je9t542s9lcofb2bdug5b.apps.googleusercontent.com';

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    importProvidersFrom(GoogleSigninButtonModule),
    {
      provide: SOCIAL_AUTH_CONFIG,
      useValue: {
        autoLogin: false,
        providers: [
          {
            id: GoogleLoginProvider.PROVIDER_ID,
            provider: new GoogleLoginProvider(GOOGLE_CLIENT_ID, {
              oneTapEnabled: false
            })
          }
        ],
        onError: (error: unknown) => {
          console.error('Error al iniciar sesión con Google:', error);
        }
      } as SocialAuthServiceConfig
    }
  ]
}).catch((error) => console.error('Error al iniciar la aplicación:', error));
