import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

@Injectable({ providedIn: 'root' })
export class CrudService {
  private readonly API_URL = API_URL;

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

  responderContraofertaResiduo(id: number, decision: 'aceptar' | 'rechazar'): Observable<any> {
    return this.http.patch(`${this.API_URL}residuos/${id}/responder-contraoferta/`, { decision });
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

  listarSolicitudesSensor(): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}solicitudes-sensor/`);
  }

  confirmarEntregaSensor(idSolicitud: number): Observable<any> {
    return this.http.post(`${this.API_URL}solicitudes-sensor/${idSolicitud}/confirmar-entrega/`, {});
  }

  conectarSensorThingSpeak(idSensor: number, datos: { thingspeak_channel_id: string; thingspeak_read_api_key?: string }): Observable<any> {
    return this.http.post(`${this.API_URL}sensores/${idSensor}/conectar-thingspeak/`, datos);
  }

  solicitarResiduo(datos: any): Observable<any> {
    return this.http.post(`${this.API_URL}solicitudes-residuo/`, datos);
  }

  listarSolicitudesResiduo(): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}solicitudes-residuo/`);
  }

  decidirSolicitudResiduoAuditoria(id: number, datos: any): Observable<any> {
    return this.http.patch(`${this.API_URL}solicitudes-residuo/${id}/decision/`, datos);
  }

  responderContraofertaSolicitudResiduo(id: number, decision: 'aceptar' | 'rechazar'): Observable<any> {
    return this.http.patch(`${this.API_URL}solicitudes-residuo/${id}/responder-contraoferta/`, { decision });
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

  diagnosticarCultivo(datos: any): Observable<any> {
    return this.http.post<any>(`${this.API_URL}ia-diagnostico-cultivo/`, datos);
  }

  listarRecomendacionesIa(): Observable<any[]> {
    return this.http.get<any[]>(`${this.API_URL}ia-recomendaciones/`);
  }

  obtenerReporteIa(idRecomendacion: number): Observable<Blob> {
    return this.http.get(`${this.API_URL}ia-recomendaciones/${idRecomendacion}/pdf/`, {
      responseType: 'blob',
    });
  }

  obtenerUltimaLecturaThingSpeak(): Observable<{ temperatura: number | null; humedad_ambiente: number | null }> {
    return this.http.get<{ temperatura: number | null; humedad_ambiente: number | null }>(
      `${this.API_URL}iot/ultima-lectura-thingspeak/`
    );
  }
}
