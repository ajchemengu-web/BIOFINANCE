import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../services/merchant_device_service.dart';
import 'merchant_auth_providers.dart';

/// This terminal's registered device identifier — sent as the
/// Device-Identifier header on every POST /payments/request
/// (docs/security-model.md "Merchant-side integrity"). Registering it (a
/// harmless upsert if it's already registered) happens once per sign-in,
/// same trigger as merchantProfileProvider.
final merchantDeviceIdentifierProvider = FutureProvider<String>((ref) {
  ref.watch(merchantAuthProvider.select((s) => s.isSignedIn));
  return ref.watch(merchantDeviceServiceProvider).ensureRegistered();
});
