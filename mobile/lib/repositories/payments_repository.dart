import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../models/payment_result.dart';

class PaymentsRepository {
  PaymentsRepository(this._apiClient);

  final ApiClient _apiClient;

  /// Creates a payment via BioRouter. `idempotencyKey` must be unique per
  /// user attempt — a retry with the same key returns the original
  /// transaction instead of double-charging (docs/database-schema.md §28).
  Future<PaymentResult> create({
    required String merchantId,
    required double amount,
    required String idempotencyKey,
    String currency = 'KES',
  }) async {
    final json = await _apiClient.post(
      '/payments',
      body: {'merchant_id': merchantId, 'amount': amount.toStringAsFixed(2), 'currency': currency},
      headers: {'Idempotency-Key': idempotencyKey},
    ) as Map<String, dynamic>;
    return PaymentResult.fromJson(json);
  }
}

final paymentsRepositoryProvider =
    Provider<PaymentsRepository>((ref) => PaymentsRepository(ref.watch(apiClientProvider)));
