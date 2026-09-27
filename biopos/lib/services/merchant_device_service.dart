import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../core/storage/secure_storage.dart';

const _deviceIdentifierKey = 'device_identifier';

String _generateDeviceIdentifier() {
  final now = DateTime.now().microsecondsSinceEpoch;
  final random = Random().nextInt(999999).toString().padLeft(6, '0');
  return 'biopos-$now-$random';
}

/// merchant_devices enforcement (docs/security-model.md "Merchant-side
/// integrity", §33 of the source PRD) — POST /payments/request now 403s
/// without a Device-Identifier the backend recognizes for this merchant.
/// This terminal generates one once and persists it locally; re-registering
/// it on every sign-in is a harmless upsert on the backend
/// (MerchantDeviceService.register in Python), not a duplicate.
class MerchantDeviceService {
  MerchantDeviceService({required this._apiClient, required this._storage});

  final ApiClient _apiClient;
  final TokenStorage _storage;

  Future<String> _deviceIdentifier() async {
    final existing = await _storage.read(_deviceIdentifierKey);
    if (existing != null) return existing;
    final generated = _generateDeviceIdentifier();
    await _storage.write(_deviceIdentifierKey, generated);
    return generated;
  }

  /// Registers this terminal's device identifier with the currently
  /// signed-in merchant and returns it, ready to send as Device-Identifier
  /// on POST /payments/request.
  Future<String> ensureRegistered() async {
    final deviceIdentifier = await _deviceIdentifier();
    await _apiClient.post(
      '/merchant-devices/register',
      body: {'device_identifier': deviceIdentifier},
    );
    return deviceIdentifier;
  }
}

final merchantDeviceServiceProvider = Provider<MerchantDeviceService>(
  (ref) => MerchantDeviceService(
    apiClient: ref.watch(apiClientProvider),
    storage: ref.watch(secureStorageProvider),
  ),
);
