define run_terraform
	source "./deploy-config.sh" && \
			    cd deploy && \
			    terraform init && \
			    terraform $(1) \
				-var "aws_access_key=$$AWS_ACCESS_KEY" \
				-var "aws_secret_key=$$AWS_SECRET_KEY" \
				-var "aws_region=$$AWS_REGION" \
				-var 'monitor_function_package=../dist/package-monitor.zip' \
				-var "telegram_notifier_package=../dist/package-tgm-notifier.zip" \
				-var "monitors=$$MONITORS" \
				-var "monitor_execution_timeout=$$MONITOR_EXECUTION_TIMEOUT" \
				-var "http_request_timeout=$$HTTP_REQUEST_TIMEOUT" \
				-var "cwatch_namespace=$$CWATCH_NAMESPACE" \
				-var "cwatch_latency_metric_name=$$CWATCH_LATENCY_METRIC_NAME" \
				-var "cwatch_state_metric_name=$$CWATCH_STATE_METRIC_NAME" \
				-var "cwatch_http_status_metric_name=$$CWATCH_HTTP_STATUS_METRIC_NAME" \
				-var "telegram_bot_token=$$TGM_BOT_TOKEN" \
				-var "telegram_receiver_chats=$$TGM_RECEIVER_CHATS" \
				-var "telegram_message_title=$$NOTIFY_TGM_TITLE"
endef

.DEFAULT_GOAL := package

clean-monitor		:
			  @(rm -rf dist/package-monitor.zip && \
		          rm -f requirements.txt.lock && \
		  	  rm -rf dist/package-monitor)

clean-tgm-notifier 	:
			  @(rm -rf dist/package-tgm-notifier.zip && \
			  rm -rf dist/package-tgm-notifier)

clean			: clean-monitor clean-tgm-notifier

requirements.txt.lock	: requirements.txt
	          	  @(pip install -r requirements.txt --target dist/package-monitor && \
			    cp requirements.txt requirements.txt.lock)

dist/package-monitor.zip: requirements.txt.lock lib/common.py lib/monitor.py
			  @(cp lib/common.py lib/monitor.py dist/package-monitor && \
			    cd dist/package-monitor && \
			    zip -r9 ../package-monitor.zip .)

dist/package-tgm-notifier.zip: lib/common.py lib/monitor.py
			  @(mkdir -p dist/package-tgm-notifier && \
			    cp lib/common.py lib/tgmnotify.py dist/package-tgm-notifier && \
			    cd dist/package-tgm-notifier && \
			    zip -r9 ../package-tgm-notifier.zip .)

package-monitor		: dist/package-monitor.zip
package-tgm-notifier    : dist/package-tgm-notifier.zip
package			: package-monitor package-tgm-notifier
deploy			: package
			  $(call run_terraform,"apply")

destroy			:
			  $(call run_terraform, "destroy")
