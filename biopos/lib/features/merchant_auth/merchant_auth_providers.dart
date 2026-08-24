import 'package:flutter_riverpod/flutter_riverpod.dart';

class MerchantSession {
  const MerchantSession({required this.isSignedIn, this.businessName});

  final bool isSignedIn;
  final String? businessName;

  static const signedOut = MerchantSession(isSignedIn: false);
}

/// Mock merchant sign-in — the backend has no merchant-auth endpoint yet
/// (Merchant/MerchantDevice today are created/looked up unauthenticated;
/// see docs/database-schema.md §"merchants"/"merchant_devices"). PRD §44
/// lists "merchant authentication" as an MVP requirement, so the screen
/// and state shape exist now; wiring to a real backend endpoint is
/// follow-up work once one exists.
class MerchantAuthNotifier extends StateNotifier<MerchantSession> {
  MerchantAuthNotifier() : super(MerchantSession.signedOut);

  Future<void> signIn(String businessName) async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    state = MerchantSession(isSignedIn: true, businessName: businessName);
  }

  void signOut() => state = MerchantSession.signedOut;
}

final merchantAuthProvider =
    StateNotifierProvider<MerchantAuthNotifier, MerchantSession>((ref) => MerchantAuthNotifier());
