import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type EstadoDictamen = 'ACEPTADO' | 'RECHAZADO';

export interface RegistroAdmin {
  id: number;
  username: string;
  nombre: string;
  correo: string;
  tipo_usuario: string;
  ultima_ubicacion: string | null;
  estado: string;
  comprobante_url: string;
}

export interface SolicitudSensorAdmin {
  id_solicitud_sensor: number;
  campesino_nombre: string;
  campesino_correo: string;
  ultima_ubicacion: string | null;
  tipo_sensor: string;
  fecha_entrega_deseada: string;
  motivo_rechazo: string | null;
  estado: string;
  fecha_solicitud: string;
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly API_URL = '/api/admin/';

  constructor(private http: HttpClient) {}

  listarContribuyentes(): Observable<RegistroAdmin[]> {
    return this.http.get<RegistroAdmin[]>(`${this.API_URL}contribuyentes/`);
  }

  listarAlcaldias(): Observable<RegistroAdmin[]> {
    return this.http.get<RegistroAdmin[]>(`${this.API_URL}alcaldias/`);
  }

  listarSolicitudesSensores(): Observable<SolicitudSensorAdmin[]> {
    return this.http.get<SolicitudSensorAdmin[]>(`${this.API_URL}solicitudes-sensores/`);
  }

  dictaminarContribuyente(id: number, estado: EstadoDictamen): Observable<RegistroAdmin> {
    return this.http.patch<RegistroAdmin>(`${this.API_URL}contribuyentes/${id}/dictaminar/`, { estado });
  }

  dictaminarAlcaldia(id: number, estado: EstadoDictamen): Observable<RegistroAdmin> {
    return this.http.patch<RegistroAdmin>(`${this.API_URL}alcaldias/${id}/dictaminar/`, { estado });
  }

  dictaminarSolicitudSensor(id: number, estado: EstadoDictamen, motivo_rechazo = ''): Observable<SolicitudSensorAdmin> {
    return this.http.patch<SolicitudSensorAdmin>(`${this.API_URL}solicitudes-sensores/${id}/dictaminar/`, {
      estado,
      motivo_rechazo,
    });
  }
}
