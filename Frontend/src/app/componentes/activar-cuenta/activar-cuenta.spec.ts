import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { AuthService } from '../../services/auth';
import { ActivarCuentaComponent } from './activar-cuenta';

describe('ActivarCuentaComponent', () => {
  let component: ActivarCuentaComponent;
  let fixture: ComponentFixture<ActivarCuentaComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ActivarCuentaComponent],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              queryParamMap: {
                get: () => 'token-de-prueba'
              }
            }
          }
        },
        {
          provide: AuthService,
          useValue: {
            activarCuenta: () => of({ mensaje: 'Cuenta activada.' })
          }
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ActivarCuentaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should activate the account', () => {
    expect(component.activada).toBe(true);
    expect(component.procesando).toBe(false);
  });
});
