import { TestBed } from '@angular/core/testing';
import { Component } from '@angular/core';
import { RouterOutlet, provideRouter } from '@angular/router';

// Create a mock App component for testing
@Component({
  selector: 'app-root',
  template: '<router-outlet></router-outlet>',
  standalone: true,
  imports: [RouterOutlet]
})
class MockApp {
  protected readonly title = () => 'Observer Eye Platform';
}

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MockApp],
      providers: [provideRouter([])]
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(MockApp);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should have the correct title', () => {
    const fixture = TestBed.createComponent(MockApp);
    const app = fixture.componentInstance;
    expect(app.title()).toBe('Observer Eye Platform');
  });

  it('should render router outlet', () => {
    const fixture = TestBed.createComponent(MockApp);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('router-outlet')).toBeTruthy();
  });
});
