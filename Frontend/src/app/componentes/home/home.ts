import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.html',
  styleUrl: './home.css'
})
export class HomeComponent {
  menuAbierto = false;
  constructor(private router: Router) {}

  alternarMenu(): void { this.menuAbierto = !this.menuAbierto; }
  cerrarMenu(): void { this.menuAbierto = false; }

  scrollToSection(sectionId: string): void {
    this.router.navigate([], { fragment: sectionId });

    setTimeout(() => {
      document.getElementById(sectionId)?.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    });
  }
}
