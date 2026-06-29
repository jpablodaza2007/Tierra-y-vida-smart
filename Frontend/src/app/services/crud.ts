import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class CrudService {
  private readonly API_URL = '/api/';

  constructor(private http: HttpClient) {}

  listarResiduos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}residuos/`);
  }

  listarResiduosDisponibles(): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}residuos-disponibles/`);
  }

  listarResiduosAuditoria(): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}residuos-auditoria/`);
  }

  decidirResiduoAuditoria(id: number, datos: any): Observable<any> {
    return this.http.patch(`${this.API_URL}residuos-auditoria/${id}/decision/`, datos);
  }

  crearResiduo(datos: any): Observable<any> {
    return this.http.post(`${this.API_URL}residuos/`, datos);
  }

  actualizarResiduo(id: number, datos: any): Observable<any> {
    return this.http.put(`${this.API_URL}residuos/${id}/`, datos);
  }

  eliminarResiduo(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}residuos/${id}/`);
  }

  listarSensores(): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}sensores/`);
  }

  crearSensor(datos: any): Observable<any> {
    return this.http.post(`${this.API_URL}sensores/`, datos);
  }

  actualizarSensor(id: number, datos: any): Observable<any> {
    return this.http.put(`${this.API_URL}sensores/${id}/`, datos);
  }

  eliminarSensor(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}sensores/${id}/`);
  }

  solicitarSensor(datos: any): Observable<any> {
    return this.http.post(`${this.API_URL}solicitudes-sensor/`, datos);
  }

  solicitarResiduo(datos: any): Observable<any> {
    return this.http.post(`${this.API_URL}solicitudes-residuo/`, datos);
  }

  listarSolicitudesResiduo(): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}solicitudes-residuo/`);
  }

  listarGestiones(): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}gestiones/`);
  }

  listarMisAsignaciones(): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}mis-asignaciones/`);
  }

  crearGestion(datos: any): Observable<any> {
    return this.http.post(`${this.API_URL}gestiones/`, datos);
  }

  actualizarGestion(id: number, datos: any): Observable<any> {
    return this.http.put(`${this.API_URL}gestiones/${id}/`, datos);
  }

  eliminarGestion(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}gestiones/${id}/`);
  }

  opcionesLogistica(): Observable<any> {
    return this.http.get(`${this.API_URL}opciones-logistica/`);
  }

  listarCampesinos(): Observable<any> {
    return this.http.get<any>(`${this.API_URL}opciones-logistica/`);
  }

  listarInventario(): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}inventario-alcaldia/`);
  }
}
