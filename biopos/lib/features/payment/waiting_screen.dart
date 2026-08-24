import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/payment_request_result.dart';
import '../../repositories/payment_requests_repository.dart';
import '../receipt/receipt_screen.dart';

/// "WAITING FOR CUSTOMER" (PRD §32). Polls GET /payments/{id} until the
/// customer claims and it resolves (or fails) on their own device — see
/// backend/app/api/payments.py POST /payments/{id}/claim, called from
/// mobile/, not from here.
class WaitingScreen extends ConsumerStatefulWidget {
  const WaitingScreen({super.key, required this.initial});

  final PaymentRequestResult initial;

  @override
  ConsumerState<WaitingScreen> createState() => _WaitingScreenState();
}

class _WaitingScreenState extends ConsumerState<WaitingScreen> {
  static const _pollInterval = Duration(seconds: 2);
  static const _slowThreshold = Duration(seconds: 30);

  late PaymentRequestResult _current;
  Timer? _pollTimer;
  bool _cancelling = false;
  bool _showSlowNotice = false;
  final _stopwatch = Stopwatch()..start();

  @override
  void initState() {
    super.initState();
    _current = widget.initial;
    _pollTimer = Timer.periodic(_pollInterval, (_) => _poll());
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _poll() async {
    if (!mounted) return;
    try {
      final result =
          await ref.read(paymentRequestsRepositoryProvider).getStatus(_current.id);
      if (!mounted) return;
      setState(() {
        _current = result;
        _showSlowNotice = _stopwatch.elapsed > _slowThreshold;
      });
      if (result.isTerminal) {
        _pollTimer?.cancel();
        Navigator.of(context).pushReplacement(
          MaterialPageRoute<void>(builder: (_) => ReceiptScreen(result: result)),
        );
      }
    } catch (_) {
      // Transient network hiccup — the next poll will retry. Not surfaced
      // to avoid flashing an error on every brief blip.
    }
  }

  Future<void> _cancel() async {
    setState(() => _cancelling = true);
    _pollTimer?.cancel();
    try {
      await ref.read(paymentRequestsRepositoryProvider).cancel(_current.id);
    } catch (_) {
      // Best-effort — leaving the screen either way.
    }
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      child: Scaffold(
        body: SafeArea(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'KSh ${_current.amount.toStringAsFixed(2)}',
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
                  const SizedBox(height: 8),
                  Text(
                    'Ref: ${_current.id}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  if (_showSlowNotice) ...[
                    const SizedBox(height: 24),
                    Text(
                      'Still waiting — the customer may not have their app open.',
                      style: Theme.of(context).textTheme.bodySmall,
                      textAlign: TextAlign.center,
                    ),
                  ],
                  const SizedBox(height: 48),
                  TextButton(
                    onPressed: _cancelling ? null : _cancel,
                    child: _cancelling
                        ? const SizedBox(
                            height: 16,
                            width: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Cancel'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
