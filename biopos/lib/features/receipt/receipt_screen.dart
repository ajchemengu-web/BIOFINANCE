import 'package:flutter/material.dart';

import '../../models/payment_request_result.dart';

/// "PAYMENT SUCCESSFUL" receipt (PRD §32).
class ReceiptScreen extends StatelessWidget {
  const ReceiptScreen({super.key, required this.result});

  final PaymentRequestResult result;

  @override
  Widget build(BuildContext context) {
    final success = result.isSuccessful;

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
                const SizedBox(height: 4),
                Text(result.status, style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: 16),
                Text(
                  'KSh ${result.amount.toStringAsFixed(2)}',
                  style: Theme.of(context).textTheme.displaySmall,
                ),
                const SizedBox(height: 8),
                Text(result.id, style: Theme.of(context).textTheme.bodyMedium),
                if (result.selectedProvider != null) ...[
                  const SizedBox(height: 4),
                  Text('via ${result.selectedProvider}'),
                ],
                const SizedBox(height: 48),
                FilledButton(
                  onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
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
