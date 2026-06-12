import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private API_URL = 'http://127.0.0.1:8000/api/auth/';

  constructor(private http: HttpClient) { }

  registrar(usuario: any): Observable<any> {
    return this.http.post(`${this.API_URL}register/`, usuario);
  }

  login(credenciales: any): Observable<any> {
    return this.http.post(`${this.API_URL}login/`, credenciales);
  }

  loginConGoogle(idToken: string): Observable<any> {
    return this.http.post(`${this.API_URL}google/`, { token: idToken });
  }

  guardarToken(token: string): void {
    localStorage.setItem('access_token', token);
  }
}
