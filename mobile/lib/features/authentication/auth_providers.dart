import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/errors/app_exception.dart';
import '../../services/auth_service.dart';

class AuthState {
  const AuthState({this.isAuthenticated = false, this.isLoading = false, this.error, this.email});

  final bool isAuthenticated;
  final bool isLoading;
  final String? error;
  final String? email;

  AuthState copyWith({bool? isAuthenticated, bool? isLoading, String? error, String? email}) =>
      AuthState(
        isAuthenticated: isAuthenticated ?? this.isAuthenticated,
        isLoading: isLoading ?? this.isLoading,
        error: error,
        email: email ?? this.email,
      );
}

/// Session state backed by the real backend (POST /auth/login, falling back
/// to /auth/register — see auth_service.dart). Screens watch this to decide
/// between LoginScreen and HomeShell (main.dart's AuthGate).
class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier(this._authService) : super(const AuthState()) {
    _restoreSession();
  }

  final AuthService _authService;

  Future<void> _restoreSession() async {
    final token = await _authService.restoreSession();
    if (token != null) state = state.copyWith(isAuthenticated: true);
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      await _authService.loginOrRegister(email, password);
      state = AuthState(isAuthenticated: true, email: email);
    } on ApiException catch (e) {
      state = state.copyWith(isLoading: false, error: e.message);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Could not reach the BioFinance server');
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    state = const AuthState();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(ref.watch(authServiceProvider)),
);
