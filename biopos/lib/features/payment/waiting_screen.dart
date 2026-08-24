import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../receipt/receipt_screen.dart';
import 'payment_providers.dart';

/// "WAITING FOR CUSTOMER" (PRD §32). In a real deployment the customer
/// authenticates on their own BioFinance app and this screen polls
/// GET /payments/{id} for the result; there's no second device here, so
/// the button below stands in for that (see payment_providers.dart).
class WaitingScreen extends ConsumerStatefulWidget {
  const WaitingScreen({super.key});

  @override
  ConsumerState<WaitingScreen> createState() => _WaitingScreenState();
}

class _WaitingScreenState extends ConsumerState<WaitingScreen> {
  bool _processing = false;

  Future<void> _simulateCustomer() async {
    setState(() => _processing = true);
    await ref.read(paymentRequestProvider.notifier).simulateCustomerAuthentication();
    if (!mounted) return;
    setState(() => _processing = false);
    Navigator.of(context).pushReplacement(
      MaterialPageRoute<void>(builder: (_) => const ReceiptScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final request = ref.watch(paymentRequestProvider);
    if (request == null) {
      // Reached directly (e.g. hot restart mid-flow) — nothing to show.
      return Scaffold(body: Center(child: TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Back'))));
    }

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'KSh ${request.amount.toStringAsFixed(2)}',
                  style: Theme.of(context).textTheme.displayMedium,
                ),
                const SizedBox(height: 24),
                const SizedBox(
                  width: 64,
                  height: 64,
                  child: CircularProgressIndicator(strokeWidth: 3),
                ),
                const SizedBox(height: 24),
                Text('WAITING FOR CUSTOMER', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 4),
                const Text('Authenticate with BioFinance'),
                const SizedBox(height: 48),
                FilledButton.icon(
                  onPressed: _processing ? null : _simulateCustomer,
                  icon: _processing
                      ? const SizedBox(
                          height: 16,
                          width: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.fingerprint),
                  label: Text(_processing ? 'Authorizing…' : 'Simulate Customer Authentication'),
                ),
                const SizedBox(height: 8),
                Text(
                  'No second device in this demo — the real flow has the customer\n'
                  'authenticate on their own BioFinance app.',
                  style: Theme.of(context).textTheme.bodySmall,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: () {
                    ref.read(paymentRequestProvider.notifier).cancel();
                    Navigator.of(context).pop();
                  },
                  child: const Text('Cancel'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
