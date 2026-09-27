import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../models/payment_request_result.dart';

String _generateIdempotencyKey() {
  final now = DateTime.now();
  final datePart =
      '${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}';
  final random = Random().nextInt(999999).toString().padLeft(6, '0');
  return 'TX-$datePart-$random';
}

/// POST /payments/request + GET /payments/{id} — see
/// backend/app/api/payments.py. Claiming (POST /payments/{id}/claim)
/// deliberately isn't here: that's the customer's own app's job
/// (mobile/lib/repositories/payments_repository.dart), called from their
/// own authenticated session, not from BioPOS.
class PaymentRequestsRepository {
  PaymentRequestsRepository(this._apiClient);

  final ApiClient _apiClient;

  /// merchant_id is no longer sent here — the backend derives it from the
  /// merchant's own bearer token (ApiClient attaches it automatically once
  /// signed in). deviceIdentifier must be one this merchant has registered
  /// via POST /merchant-devices/register (docs/roadmap.md Phase 5,
  /// "merchant_devices enforcement") — the caller gets it from
  /// merchantDeviceIdentifierProvider.
  Future<PaymentRequestResult> create({required String deviceIdentifier, required double amount}) async {
    final json = await _apiClient.post(
      '/payments/request',
      body: {'amount': amount.toStringAsFixed(2), 'currency': 'KES'},
      headers: {
        'Idempotency-Key': _generateIdempotencyKey(),
        'Device-Identifier': deviceIdentifier,
      },
    ) as Map<String, dynamic>;
    return PaymentRequestResult.fromJson(json);
  }

  Future<PaymentRequestResult> getStatus(String paymentId) async {
    final json = await _apiClient.get('/payments/$paymentId') as Map<String, dynamic>;
    return PaymentRequestResult.fromJson(json);
  }

  /// Now requires the owning merchant's bearer token too (docs/roadmap.md
  /// Phase 5) — no header change needed here, ApiClient attaches it
  /// automatically for every request once signed in.
  Future<PaymentRequestResult> cancel(String paymentId) async {
    final json = await _apiClient.post('/payments/$paymentId/cancel') as Map<String, dynamic>;
    return PaymentRequestResult.fromJson(json);
  }
}

final paymentRequestsRepositoryProvider = Provider<PaymentRequestsRepository>(
  (ref) => PaymentRequestsRepository(ref.watch(apiClientProvider)),
);
