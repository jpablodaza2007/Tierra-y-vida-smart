import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { Router } from '@angular/router';

export interface SesionUsuario {
  nombre: string;
  email: string;
  rol: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly API_URL = '/api/auth/';

  constructor(
    private http: HttpClient,
    private router: Router
  ) { }

  registrar(usuario: any): Observable<any> {
    return this.http.post(`${this.API_URL}register/`, usuario);
  }

  login(credenciales: any): Observable<any> {
    return this.http.post(`${this.API_URL}login/`, credenciales);
  }

  loginConGoogle(idToken: string): Observable<any> {
    return this.http.post(`${this.API_URL}google/`, { token: idToken });
  }

  activarCuenta(token: string): Observable<any> {
    const params = new HttpParams().set('token', token);
    return this.http.get(`${this.API_URL}activate/`, { params });
  }

  guardarTokens(accessToken: string, refreshToken?: string): void {
    localStorage.setItem('access_token', accessToken);

    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
  }

  guardarAccessToken(accessToken: string): void {
    localStorage.setItem('access_token', accessToken);
  }

  guardarSesion(respuesta: any): void {
    this.guardarTokens(respuesta.access, respuesta.refresh);
    const usuario: SesionUsuario = {
      nombre: respuesta.nombre || '',
      email: respuesta.email || '',
      rol: respuesta.rol || ''
    };
    localStorage.setItem('usuario', JSON.stringify(usuario));
  }

  obtenerUsuario(): SesionUsuario | null {
    const usuario = localStorage.getItem('usuario');
    return usuario ? JSON.parse(usuario) : null;
  }

  obtenerToken(): string | null {
    return localStorage.getItem('access_token');
  }

  obtenerRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  obtenerPerfil(): Observable<any> {
    return this.http.get(`${this.API_URL}profile/`);
  }

  limpiarSesion(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('usuario');
  }

  validarSesion(): Observable<boolean> {
    const token = this.obtenerToken();
    const usuario = this.obtenerUsuario();

    if (!token || !usuario) {
      this.limpiarSesion();
      return of(false);
    }

    return this.obtenerPerfil().pipe(
      map(() => true),
      catchError(() => {
        this.limpiarSesion();
        return of(false);
      })
    );
  }

  rutaPorRol(rol?: string): string {
    const rolNormalizado = (rol || this.obtenerUsuario()?.rol || '').toLowerCase();
    if (rolNormalizado === 'admin') return '/admin';
    if (rolNormalizado === 'campesino') return '/campesino';
    if (rolNormalizado === 'alcaldia' || rolNormalizado === 'alcaldía') return '/alcaldia';
    return '/contribuyente';
  }

  irAlPanel(): void {
    this.router.navigate([this.rutaPorRol()]);
  }

  cerrarSesion(): void {
    this.limpiarSesion();
    this.router.navigate(['/login']).catch(() => {});
    window.location.href = '/login';
  }
}
