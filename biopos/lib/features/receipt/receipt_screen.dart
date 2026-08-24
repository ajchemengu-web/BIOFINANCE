import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/pos_transaction.dart';
import '../payment/payment_providers.dart';

/// "PAYMENT SUCCESSFUL" receipt (PRD §32).
class ReceiptScreen extends ConsumerWidget {
  const ReceiptScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final request = ref.watch(paymentRequestProvider);
    final success = request?.status == PosTransactionStatus.completed;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  success ? Icons.check_circle : Icons.cancel,
                  color: success ? Colors.green : Colors.red,
                  size: 96,
                ),
                const SizedBox(height: 16),
                Text(
                  success ? 'PAYMENT SUCCESSFUL' : 'PAYMENT NOT COMPLETED',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: 16),
                if (request != null) ...[
                  Text(
                    'KSh ${request.amount.toStringAsFixed(2)}',
                    style: Theme.of(context).textTheme.displaySmall,
                  ),
                  const SizedBox(height: 8),
                  Text(request.id, style: Theme.of(context).textTheme.bodyMedium),
                ],
                const SizedBox(height: 48),
                FilledButton(
                  onPressed: () {
                    ref.read(paymentRequestProvider.notifier).reset();
                    Navigator.of(context).popUntil((route) => route.isFirst);
                  },
                  child: const Text('New Transaction'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
