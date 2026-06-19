import { Routes } from '@angular/router';
import { authGuard } from './services/auth.guard';

export const routes: Routes = [
    {
        path: '',
        redirectTo: 'login',
        pathMatch: 'full'
    },
    {
        path: 'login',
        loadComponent: () => import('./componentes/login/login').then(m => m.LoginComponent),
        title: "Iniciar Sesión"
    },
    {
        path: 'registro',
        loadComponent: () => import('./componentes/registro/registro').then(m => m.RegistroComponent),
        title: "Registro de Usuario"
    },
    {
        path: 'activar-cuenta',
        loadComponent: () => import('./componentes/activar-cuenta/activar-cuenta').then(m => m.ActivarCuentaComponent),
        title: "Activar Cuenta"
    },
    {
        path: 'contribuyente',
        loadComponent: () => import('./componentes/panel-contribuyente/panel-contribuyente').then(m => m.PanelContribuyenteComponent),
        canActivate: [authGuard],
        data: { roles: ['contribuyente'] },
        title: 'Panel del Contribuyente'
    },
    {
        path: 'campesino',
        loadComponent: () => import('./componentes/panel-campesino/panel-campesino').then(m => m.PanelCampesinoComponent),
        canActivate: [authGuard],
        data: { roles: ['campesino'] },
        title: 'Panel del Campesino'
    },
    {
        path: 'alcaldia',
        loadComponent: () => import('./componentes/panel-alcaldia/panel-alcaldia').then(m => m.PanelAlcaldiaComponent),
        canActivate: [authGuard],
        data: { roles: ['alcaldia'] },
        title: 'Panel de Alcaldía'
    },
    {
        path: '**',
        redirectTo: 'login'
    }
];
