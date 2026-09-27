import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/errors/app_exception.dart';
import '../../services/merchant_auth_service.dart';

class MerchantSession {
  const MerchantSession({this.isSignedIn = false, this.isLoading = false, this.error});

  final bool isSignedIn;
  final bool isLoading;
  final String? error;

  MerchantSession copyWith({bool? isLoading, String? error}) =>
      MerchantSession(isSignedIn: isSignedIn, isLoading: isLoading ?? this.isLoading, error: error);
}

/// Session state backed by the real backend (POST /merchants/login, falling
/// back to /merchants/register — see merchant_auth_service.dart). Mirrors
/// mobile/lib/features/authentication/auth_providers.dart exactly: this
/// only tracks whether a session exists, not the merchant's own profile —
/// that's merchantProfileProvider (merchant_profile_providers.dart), fetched
/// fresh once signed in, same shape as mobile/'s bioIdProvider.
class MerchantAuthNotifier extends StateNotifier<MerchantSession> {
  MerchantAuthNotifier(this._authService) : super(const MerchantSession()) {
    _restoreSession();
  }

  final MerchantAuthService _authService;

  Future<void> _restoreSession() async {
    final token = await _authService.restoreSession();
    if (token != null) state = const MerchantSession(isSignedIn: true);
  }

  Future<void> signIn(String businessName, String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      await _authService.loginOrRegister(businessName, email, password);
      state = const MerchantSession(isSignedIn: true);
    } on ApiException catch (e) {
      state = state.copyWith(isLoading: false, error: e.message);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Could not reach the BioFinance server');
    }
  }

  Future<void> signOut() async {
    await _authService.logout();
    state = const MerchantSession();
  }
}

final merchantAuthProvider = StateNotifierProvider<MerchantAuthNotifier, MerchantSession>(
  (ref) => MerchantAuthNotifier(ref.watch(merchantAuthServiceProvider)),
);
