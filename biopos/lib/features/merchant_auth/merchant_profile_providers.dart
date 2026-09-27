import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/merchant.dart';
import '../../repositories/merchants_repository.dart';
import 'merchant_auth_providers.dart';

/// The signed-in merchant's own profile (GET /merchants/me) — fetched fresh
/// once signed in, re-fetched whenever the session's signed-in status
/// flips. Same pattern as mobile/lib/features/bioid/bioid_providers.dart's
/// bioIdProvider.
final merchantProfileProvider = FutureProvider<Merchant>((ref) {
  ref.watch(merchantAuthProvider.select((s) => s.isSignedIn));
  return ref.watch(merchantsRepositoryProvider).me();
});
