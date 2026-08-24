import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/transaction.dart';
import '../dashboard/balance_providers.dart';
import '../routing/routing_policy_providers.dart';
import '../transactions/transaction_providers.dart';

enum PaymentOutcomeStatus { success, declined }

class PaymentOutcome {
  const PaymentOutcome({
    required this.status,
    required this.merchantName,
    required this.amount,
    this.provider,
    this.usedFallback = false,
  });

  final PaymentOutcomeStatus status;
  final String merchantName;
  final double amount;
  final String? provider;
  final bool usedFallback;
}

/// Mock BioRouter: attempts the primary provider, falls back per policy on
/// decline, and records the resulting transaction. Mirrors the algorithm in
/// docs/database-schema.md's state machine and PRD §23/§43. The real
/// version talks to backend/app/services/router_service.py in Phase 3 —
/// this stays local-only until then.
class PaymentNotifier extends StateNotifier<PaymentOutcome?> {
  PaymentNotifier(this._ref) : super(null);

  final Ref _ref;

  Future<PaymentOutcome> pay({required String merchantName, required double amount}) async {
    final policy = _ref.read(routingPolicyProvider);
    final balancesNotifier = _ref.read(rawBalancesProvider.notifier);

    await Future<void>.delayed(const Duration(milliseconds: 500)); // simulated authorization latency

    final primary = policy.primaryProviderCode;
    if (primary != null && balancesNotifier.debit(primary, amount)) {
      return _record(merchantName, amount, primary, usedFallback: false);
    }

    final fallback = policy.fallbackProviderCode;
    if (fallback != null && fallback != primary && balancesNotifier.debit(fallback, amount)) {
      return _record(merchantName, amount, fallback, usedFallback: true);
    }

    final outcome = PaymentOutcome(
      status: PaymentOutcomeStatus.declined,
      merchantName: merchantName,
      amount: amount,
    );
    state = outcome;
    _ref.read(transactionProvider.notifier).add(
          AppTransaction(
            id: _generateTransactionId(),
            merchantName: merchantName,
            amount: amount,
            status: TransactionStatus.declined,
            provider: primary ?? 'NONE',
            createdAt: DateTime.now(),
          ),
        );
    return outcome;
  }

  PaymentOutcome _record(String merchantName, double amount, String provider, {required bool usedFallback}) {
    final outcome = PaymentOutcome(
      status: PaymentOutcomeStatus.success,
      merchantName: merchantName,
      amount: amount,
      provider: provider,
      usedFallback: usedFallback,
    );
    state = outcome;
    _ref.read(transactionProvider.notifier).add(
          AppTransaction(
            id: _generateTransactionId(),
            merchantName: merchantName,
            amount: amount,
            status: TransactionStatus.completed,
            provider: provider,
            createdAt: DateTime.now(),
          ),
        );
    return outcome;
  }
}

String _generateTransactionId() {
  final now = DateTime.now();
  final datePart =
      '${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}';
  final timePart = now.millisecondsSinceEpoch.remainder(1000000).toString().padLeft(6, '0');
  return 'TX-$datePart-$timePart';
}

final paymentProvider = StateNotifierProvider<PaymentNotifier, PaymentOutcome?>(
  (ref) => PaymentNotifier(ref),
);
