import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/errors/app_exception.dart';
import '../../repositories/merchants_repository.dart';
import '../../repositories/payments_repository.dart';
import '../dashboard/balance_providers.dart';
import '../transactions/transaction_providers.dart';

enum PaymentOutcomeStatus { success, declined, error }

class PaymentOutcome {
  const PaymentOutcome({
    required this.status,
    required this.merchantName,
    required this.amount,
    this.provider,
    this.message,
  });

  final PaymentOutcomeStatus status;
  final String merchantName;
  final double amount;
  final String? provider;
  final String? message;
}

String _generateIdempotencyKey() {
  final now = DateTime.now();
  final datePart =
      '${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}';
  final random = Random().nextInt(999999).toString().padLeft(6, '0');
  return 'TX-$datePart-$random';
}

/// Calls the real backend: creates a merchant record for the demo (Phase 5's
/// BioPOS will own this for real), then POST /payments — BioRouter on the
/// server does the actual primary/fallback provider selection now, unlike
/// the Phase 1 mock which simulated routing client-side.
class PaymentNotifier extends StateNotifier<PaymentOutcome?> {
  PaymentNotifier(this._ref) : super(null);

  final Ref _ref;

  Future<PaymentOutcome> pay({required String merchantName, required double amount}) async {
    try {
      final merchant = await _ref.read(merchantsRepositoryProvider).create(merchantName);
      final result = await _ref.read(paymentsRepositoryProvider).create(
            merchantId: merchant.id,
            amount: amount,
            idempotencyKey: _generateIdempotencyKey(),
          );

      _ref.invalidate(balanceProvider);
      _ref.invalidate(transactionProvider);

      final outcome = PaymentOutcome(
        status: result.status == 'COMPLETED' ? PaymentOutcomeStatus.success : PaymentOutcomeStatus.declined,
        merchantName: merchantName,
        amount: amount,
        provider: result.selectedProvider,
        message: result.status == 'COMPLETED' ? null : 'No connected provider had sufficient funds.',
      );
      state = outcome;
      return outcome;
    } on ApiException catch (e) {
      final outcome = PaymentOutcome(
        status: PaymentOutcomeStatus.error,
        merchantName: merchantName,
        amount: amount,
        message: e.message,
      );
      state = outcome;
      return outcome;
    } catch (e) {
      final outcome = PaymentOutcome(
        status: PaymentOutcomeStatus.error,
        merchantName: merchantName,
        amount: amount,
        message: 'Could not reach the BioFinance server',
      );
      state = outcome;
      return outcome;
    }
  }
}

final paymentProvider = StateNotifierProvider<PaymentNotifier, PaymentOutcome?>(
  (ref) => PaymentNotifier(ref),
);
