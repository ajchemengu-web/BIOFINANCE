import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../merchant_auth/merchant_auth_providers.dart';
import '../payment/payment_providers.dart';
import '../payment/waiting_screen.dart';

/// Merchant enters an amount and requests payment (PRD §32).
class AmountEntryScreen extends ConsumerStatefulWidget {
  const AmountEntryScreen({super.key});

  @override
  ConsumerState<AmountEntryScreen> createState() => _AmountEntryScreenState();
}

class _AmountEntryScreenState extends ConsumerState<AmountEntryScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();

  @override
  void dispose() {
    _amountController.dispose();
    super.dispose();
  }

  void _requestPayment() {
    if (!_formKey.currentState!.validate()) return;
    final amount = double.parse(_amountController.text);
    ref.read(paymentRequestProvider.notifier).create(amount);
    Navigator.of(context)
        .push(MaterialPageRoute<void>(builder: (_) => const WaitingScreen()))
        .then((_) => _amountController.clear());
  }

  @override
  Widget build(BuildContext context) {
    final merchant = ref.watch(merchantAuthProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('BioPOS'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sign out',
            onPressed: () => ref.read(merchantAuthProvider.notifier).signOut(),
          ),
        ],
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  merchant.businessName ?? '',
                  style: Theme.of(context).textTheme.titleMedium,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                TextFormField(
                  controller: _amountController,
                  autofocus: true,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.displaySmall,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    prefixText: 'KSh ',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    final amount = double.tryParse(value ?? '');
                    if (amount == null || amount <= 0) return 'Enter a valid amount';
                    return null;
                  },
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: _requestPayment,
                  icon: const Icon(Icons.fingerprint),
                  label: const Text('Request Payment'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
