import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/errors/app_exception.dart';
import '../../repositories/payment_requests_repository.dart';
import '../merchant_auth/merchant_auth_providers.dart';
import '../payment/waiting_screen.dart';

/// Merchant enters an amount and opens a payment request (PRD §32) via
/// POST /payments/request.
class AmountEntryScreen extends ConsumerStatefulWidget {
  const AmountEntryScreen({super.key});

  @override
  ConsumerState<AmountEntryScreen> createState() => _AmountEntryScreenState();
}

class _AmountEntryScreenState extends ConsumerState<AmountEntryScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  bool _submitting = false;

  @override
  void dispose() {
    _amountController.dispose();
    super.dispose();
  }

  Future<void> _requestPayment() async {
    if (!_formKey.currentState!.validate()) return;
    final merchantId = ref.read(merchantAuthProvider).merchantId;
    if (merchantId == null) return;

    setState(() => _submitting = true);
    try {
      final amount = double.parse(_amountController.text);
      final request = await ref
          .read(paymentRequestsRepositoryProvider)
          .create(merchantId: merchantId, amount: amount);

      if (!mounted) return;
      setState(() => _submitting = false);
      await Navigator.of(context).push(
        MaterialPageRoute<void>(builder: (_) => WaitingScreen(initial: request)),
      );
      _amountController.clear();
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _submitting = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } catch (_) {
      if (!mounted) return;
      setState(() => _submitting = false);
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Could not reach the BioFinance server')));
    }
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
                  onPressed: _submitting ? null : _requestPayment,
                  icon: _submitting
                      ? const SizedBox(
                          height: 16,
                          width: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.fingerprint),
                  label: Text(_submitting ? 'Creating request…' : 'Request Payment'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
