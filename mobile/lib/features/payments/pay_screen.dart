import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/security/biometric_auth.dart';
import 'payment_providers.dart';

/// Mock end-to-end payment journey (PRD §42): amount entry → biometric
/// authentication → mock BioRouter → result. No backend call yet — see
/// payment_providers.dart for the mock routing/fallback logic.
class PayScreen extends ConsumerStatefulWidget {
  const PayScreen({super.key});

  @override
  ConsumerState<PayScreen> createState() => _PayScreenState();
}

class _PayScreenState extends ConsumerState<PayScreen> {
  final _formKey = GlobalKey<FormState>();
  final _merchantController = TextEditingController(text: 'Java House');
  final _amountController = TextEditingController(text: '450');
  bool _processing = false;

  @override
  void dispose() {
    _merchantController.dispose();
    _amountController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _processing = true);

    final biometricAuth = ref.read(biometricAuthProvider);
    var biometricOk = true;
    try {
      if (await biometricAuth.isAvailable()) {
        biometricOk = await biometricAuth.authenticate(reason: 'Authenticate to pay');
      }
    } catch (_) {
      // No biometric hardware on this device/emulator — proceed for the demo.
      biometricOk = true;
    }

    if (!biometricOk) {
      setState(() => _processing = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Biometric authentication failed')),
        );
      }
      return;
    }

    final outcome = await ref.read(paymentProvider.notifier).pay(
          merchantName: _merchantController.text,
          amount: double.parse(_amountController.text),
        );

    if (!mounted) return;
    setState(() => _processing = false);

    // Show the result while PayScreen is still on the stack (its context is
    // still valid here) — the OK button pops both the dialog and this
    // screen, returning to the dashboard.
    final success = outcome.status == PaymentOutcomeStatus.success;
    await showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        icon: Icon(
          success ? Icons.check_circle : Icons.cancel,
          color: success ? Colors.green : Colors.red,
          size: 48,
        ),
        title: Text(success ? 'PAYMENT SUCCESSFUL' : 'PAYMENT DECLINED'),
        content: Text(
          success
              ? 'KSh ${outcome.amount.toStringAsFixed(2)} to ${outcome.merchantName}'
                  '${outcome.usedFallback ? '\n(routed via fallback provider)' : ''}'
              : 'No connected provider had sufficient funds.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Pay')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                controller: _merchantController,
                decoration: const InputDecoration(labelText: 'Merchant', border: OutlineInputBorder()),
                validator: (value) => (value == null || value.isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _amountController,
                decoration: const InputDecoration(
                  labelText: 'Amount (KSh)',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                validator: (value) {
                  final amount = double.tryParse(value ?? '');
                  if (amount == null || amount <= 0) return 'Enter a valid amount';
                  return null;
                },
              ),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: _processing ? null : _submit,
                icon: _processing
                    ? const SizedBox(
                        height: 16,
                        width: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.fingerprint),
                label: Text(_processing ? 'Authorizing…' : 'Authenticate & Pay'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
