import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../services/bioid_service.dart';

class AuthState {
  const AuthState({required this.isAuthenticated, this.email, this.fullName, this.bioIdCode});

  final bool isAuthenticated;
  final String? email;
  final String? fullName;
  final String? bioIdCode;

  static const unauthenticated = AuthState(isAuthenticated: false);
}

/// Mock session state for Phase 1. Real login/register calls the backend in
/// Phase 2 (docs/roadmap.md); this notifier keeps the same public API
/// (`login`/`logout`) so screens don't change when that lands.
class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier() : super(AuthState.unauthenticated);

  Future<void> login(String email, String password) async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    state = AuthState(
      isAuthenticated: true,
      email: email,
      fullName: email.split('@').first,
      bioIdCode: generateBioIdCode(),
    );
  }

  void logout() => state = AuthState.unauthenticated;
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) => AuthNotifier());
