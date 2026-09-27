import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/errors/app_exception.dart';
import '../../repositories/payment_requests_repository.dart';
import '../merchant_auth/merchant_auth_providers.dart';
import '../merchant_auth/merchant_device_providers.dart';
import '../merchant_auth/merchant_profile_providers.dart';
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

    setState(() => _submitting = true);
    try {
      // Device-Identifier is required now (merchant_devices enforcement,
      // docs/roadmap.md Phase 5) — this terminal registered itself on
      // sign-in (merchantDeviceIdentifierProvider), so this just awaits
      // that same in-flight/cached future rather than re-registering.
      final deviceIdentifier = await ref.read(merchantDeviceIdentifierProvider.future);
      final amount = double.parse(_amountController.text);
      final request = await ref
          .read(paymentRequestsRepositoryProvider)
          .create(deviceIdentifier: deviceIdentifier, amount: amount);

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
    final merchantAsync = ref.watch(merchantProfileProvider);

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
                merchantAsync.when(
                  data: (merchant) => Text(
                    merchant.businessName,
                    style: Theme.of(context).textTheme.titleMedium,
                    textAlign: TextAlign.center,
                  ),
                  loading: () => const SizedBox.shrink(),
                  error: (_, __) => const SizedBox.shrink(),
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
