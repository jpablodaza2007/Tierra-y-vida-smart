import { Routes } from '@angular/router';
import { LoginComponent } from './componentes/login/login';
import { RegistroComponent } from './componentes/registro/registro';

export const routes: Routes = [
    { path: '', redirectTo: 'login', pathMatch: 'full' },
    { path: 'login', component: LoginComponent },
    { path: 'registro', component: RegistroComponent },
    { path: '**', redirectTo: 'login' }
];
